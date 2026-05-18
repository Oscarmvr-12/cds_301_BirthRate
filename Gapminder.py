import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State

file_path = "P_Data_Extract_From_World_Development_Indicators.xlsx"

data = pd.read_excel(file_path, sheet_name="Data", engine="openpyxl")

codes = {
    "total_mortality": "SP.DYN.IMRT.IN",
    "male_mortality": "SP.DYN.IMRT.MA.IN",
    "female_mortality": "SP.DYN.IMRT.FE.IN"
}

year_cols = [col for col in data.columns if "[YR" in col]


def clean_indicator(series_code, value_name):
    temp = data[data["Series Code"] == series_code].copy()
    temp = temp[["Country Name", "Country Code"] + year_cols]

    temp = temp.melt(
        id_vars=["Country Name", "Country Code"],
        value_vars=year_cols,
        var_name="year",
        value_name=value_name
    )

    temp["year"] = temp["year"].str.extract(r"(\d{4})").astype(int)

    temp[value_name] = pd.to_numeric(
        temp[value_name].replace("..", pd.NA),
        errors="coerce"
    )

    return temp


total = clean_indicator(codes["total_mortality"], "total_mortality")
male = clean_indicator(codes["male_mortality"], "male_mortality")
female = clean_indicator(codes["female_mortality"], "female_mortality")

df = total.merge(
    male,
    on=["Country Name", "Country Code", "year"],
    how="inner"
)

df = df.merge(
    female,
    on=["Country Name", "Country Code", "year"],
    how="inner"
)

df = df.dropna(
    subset=["total_mortality", "male_mortality", "female_mortality"]
)

df = df[
    (df["year"] >= 1960) &
    (df["year"] <= 2024)
].copy()

df["mortality_gap"] = df["male_mortality"] - df["female_mortality"]

df["total_mortality"] = df["total_mortality"].round(1)
df["male_mortality"] = df["male_mortality"].round(1)
df["female_mortality"] = df["female_mortality"].round(1)
df["mortality_gap"] = df["mortality_gap"].round(2)

world_url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(world_url)

regions = world[["ADM0_A3", "CONTINENT"]].rename(
    columns={
        "ADM0_A3": "Country Code",
        "CONTINENT": "region"
    }
)

df = df.merge(regions, on="Country Code", how="left")
df["region"] = df["region"].fillna("Other")

valid_regions = sorted(
    region for region in df["region"].dropna().unique()
    if region not in ["Antarctica", "Seven seas (open ocean)"]
)

region_options = [{"label": "All Regions", "value": "All"}] + [
    {"label": region, "value": region}
    for region in valid_regions
]

country_options = [
    {"label": country, "value": country}
    for country in sorted(df["Country Name"].dropna().unique())
]

region_colors = {
    "Africa": "#9f5f4f",
    "Asia": "#176b5c",
    "Europe": "#4d7188",
    "North America": "#7c6a93",
    "South America": "#aa7d2a",
    "Oceania": "#4f9d8a",
    "Other": "#918b82"
}

label_positions = [
    "top center",
    "bottom center",
    "middle right",
    "middle left"
]

app = Dash(__name__)
server = app.server

app.layout = html.Div(
    style={"fontFamily": "Inter, Arial, sans-serif", "margin": "0", "padding": "0", "backgroundColor": "#f7f5f0", "color": "#181716"},
    children=[
        html.Div(
            style={"display": "flex", "height": "100vh"},
            children=[
                html.Div(
                    style={
                        "width": "330px",
                        "padding": "20px",
                        "borderRight": "1px solid #ded8ce",
                        "boxSizing": "border-box",
                        "overflowY": "auto",
                        "backgroundColor": "#fffdfa"
                    },
                    children=[
                        html.Label("Regions", style={"fontWeight": "bold"}),

                        dcc.Dropdown(
                            id="region-dropdown",
                            options=region_options,
                            value=[],
                            multi=True,
                            clearable=True,
                            searchable=True,
                            placeholder="Choose region(s)...",
                            style={"marginTop": "6px"}
                        ),

                        html.Br(),

                        html.Label("Highlight Countries", style={"fontWeight": "bold"}),

                        dcc.Dropdown(
                            id="country-dropdown",
                            options=country_options,
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
                            }
                        ),

                        html.Br(),

                        html.Button(
                            "Play / Pause",
                            id="play-button",
                            n_clicks=0,
                            style={
                                "width": "100%",
                                "padding": "10px",
                                "fontSize": "15px"
                            }
                        ),

                        html.Hr(),

                        html.Div(
                            "Region selection controls the background points. Country selection works independently and always shows selected country trails.",
                            style={
                                "fontSize": "14px",
                                "lineHeight": "1.4",
                                "color": "#6f6b64"
                            }
                        )
                    ]
                ),

                html.Div(
                    style={
                        "flex": "1",
                        "padding": "10px 20px",
                        "boxSizing": "border-box"
                    },
                    children=[
                        html.H1(
                            "Global Health Transition and Infant Mortality Inequality",
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
                                "color": "#6f6b64",
                                "marginBottom": "5px"
                            }
                        ),

                        dcc.Interval(
                            id="interval",
                            interval=850,
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
                                "color": "#918b82",
                                "marginTop": "-8px"
                            }
                        )
                    ]
                )
            ]
        )
    ]
)


@app.callback(
    Output("interval", "disabled"),
    Input("play-button", "n_clicks"),
    State("interval", "disabled")
)
def toggle_play(n_clicks, disabled):
    if n_clicks == 0:
        return True

    return not disabled


@app.callback(
    Output("year-slider", "value"),
    Input("interval", "n_intervals"),
    State("year-slider", "value")
)
def animate_year(n_intervals, current_year):
    if current_year >= 2024:
        return 1960

    return current_year + 1


@app.callback(
    Output("transition-graph", "figure"),
    Input("region-dropdown", "value"),
    Input("country-dropdown", "value"),
    Input("year-slider", "value")
)
def update_graph(selected_regions, selected_countries, selected_year):

    if selected_regions is None:
        selected_regions = []

    if selected_countries is None:
        selected_countries = []

    # Background points depend only on selected regions.
    if not selected_regions:
        background_data = df.iloc[0:0].copy()
    else:
        background_data = df.copy()

        if "All" not in selected_regions:
            background_data = background_data[
                background_data["region"].isin(selected_regions)
            ]

    current_background = background_data[
        background_data["year"] == selected_year
    ].copy()

    fig = go.Figure()

    # =========================
    # BACKGROUND REGION POINTS
    # =========================

    for region in sorted(current_background["region"].dropna().unique()):

        region_data = current_background[
            (current_background["region"] == region) &
            (~current_background["Country Name"].isin(selected_countries))
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
                    size=region_data["total_mortality"].clip(lower=8, upper=160) / 3.8,
                    color=region_colors.get(region, "#918b82"),
                    opacity=0.38,
                    line=dict(width=0.5, color="#fffdfa")
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
    # Country selections ignore region filter.
    # =========================

    for i, country in enumerate(selected_countries):

        country_data = df[
            (df["Country Name"] == country) &
            (df["year"] <= selected_year)
        ].copy()

        current_country = df[
            (df["Country Name"] == country) &
            (df["year"] == selected_year)
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
                    width=1.8,
                    color="rgba(111,107,100,0.55)"
                ),
                opacity=0.45,
                hoverinfo="skip",
                showlegend=False
            )
        )

        if not current_country.empty:
            region = current_country["region"].iloc[0]
            label_position = label_positions[i % len(label_positions)]

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
                        color="#181716",
                        family="Inter, Arial, sans-serif"
                    ),
                    marker=dict(
                        size=22,
                        color=region_colors.get(region, "#181716"),
                        opacity=1.0,
                        line=dict(width=2.2, color="#181716")
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

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#918b82",
        line_width=1
    )

    fig.update_layout(
        title=f"Health Transition Scatter ({selected_year})",
        title_x=0.5,
        height=720,
        plot_bgcolor="#fffdfa",
        paper_bgcolor="#fffdfa",

        xaxis=dict(
            title="Total infant mortality, deaths per 1,000 live births",
            range=[0, 230],
            automargin=True,
            gridcolor="#ded8ce",
            zeroline=False
        ),

        yaxis=dict(
            title="Male − Female infant mortality gap",
            range=[-10, 35],
            automargin=True,
            gridcolor="#ded8ce",
            zeroline=True,
            zerolinecolor="#918b82"
        ),

        legend=dict(
            title="Region / Highlighted Countries",
            x=1.02,
            y=1,
            bgcolor="rgba(255,255,255,0.85)"
        ),

        transition=dict(
            duration=500,
            easing="cubic-in-out"
        ),

        font=dict(family="Inter, Arial, sans-serif", color="#181716"),
        margin=dict(l=80, r=210, t=70, b=48)
    )

    return fig


if __name__ == "__main__":
    app.run(debug=False)
