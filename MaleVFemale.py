import os
import pandas as pd
import plotly.express as px

file_path = "P_Data_Extract_From_World_Development_Indicators.xlsx"

data = pd.read_excel(file_path, sheet_name="Data", engine="openpyxl")

male_code = "SP.DYN.IMRT.MA.IN"
female_code = "SP.DYN.IMRT.FE.IN"

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


male = clean_indicator(male_code, "male_mortality")
female = clean_indicator(female_code, "female_mortality")

gap = male.merge(
    female,
    on=["Country Name", "Country Code", "year"],
    how="inner"
)

gap = gap.dropna(subset=["male_mortality", "female_mortality"])

gap = gap[
    (gap["year"] >= 1960) &
    (gap["year"] <= 2024)
].copy()

gap["mortality_gap"] = gap["male_mortality"] - gap["female_mortality"]

gap["male_mortality"] = gap["male_mortality"].round(1)
gap["female_mortality"] = gap["female_mortality"].round(1)
gap["mortality_gap"] = gap["mortality_gap"].round(2)

fig = px.choropleth(
    gap,
    locations="Country Code",
    color="mortality_gap",
    hover_name="Country Name",
    animation_frame="year",
    animation_group="Country Name",
    color_continuous_scale=[
        [0.0, "#4d7188"],
        [0.25, "#a9c6cf"],
        [0.5, "#fffdfa"],
        [0.75, "#d7a08f"],
        [1.0, "#9f5f4f"]
    ],
    range_color=(-15, 15),
    projection="natural earth",
    hover_data={
        "Country Code": False,
        "year": True,
        "male_mortality": True,
        "female_mortality": True,
        "mortality_gap": True
    },
    labels={
        "mortality_gap": "Male − Female Gap",
        "male_mortality": "Male mortality",
        "female_mortality": "Female mortality",
        "year": "Year"
    },
    title="Male–Female Infant Mortality Gap Over Time"
)

fig.update_layout(
    title_x=0.5,
    height=740,
    margin=dict(l=10, r=10, t=70, b=10),
    paper_bgcolor="#fffdfa",
    font=dict(family="Inter, Arial, sans-serif", color="#181716"),
    coloraxis_colorbar=dict(
        title="Male − Female<br>deaths per 1,000",
        tickvals=[-15, -10, -5, 0, 5, 10, 15],
        ticktext=[
            "Female higher",
            "-10",
            "-5",
            "0",
            "+5",
            "+10",
            "Male higher"
        ]
    )
)

fig.update_geos(
    showframe=False,
    showcoastlines=True,
    coastlinecolor="#6f6b64",
    showcountries=True,
    countrycolor="#ded8ce",
    showland=True,
    landcolor="#ece7de"
)

os.makedirs("static/dashboards", exist_ok=True)

fig.write_html(
    "static/dashboards/MaleVFemale.html",
    include_plotlyjs="cdn",
    full_html=True
)

if os.environ.get("SHOW_PLOTLY_PREVIEW") == "1":
    fig.show()
