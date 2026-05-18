# Visualizing Global Development Through Demographic and Health Indicators

Course project for **CDS 301 / 501: Scientific Information and Data Visualization** at George Mason University Korea.

## Team

- Spring Park
- Joonseop Jang
- Oscar Molina Romualdo

## Project Summary

This project examines whether development can be understood more fully through social, demographic, and health indicators rather than income classifications alone. Using World Bank World Development Indicators and United Nations World Economic Situation and Prospects country groupings, the project compares fertility, infant mortality, migration, and sex-based mortality differences across countries and over time.

The website combines static figures, interactive Plotly/Dash dashboards, and bilingual English/Korean page text.

## Visualizations

- Fertility patterns across countries and development groups
- Migrant share by development group
- Geographic distribution of migrant-share outliers
- Interactive infant mortality map by year and sex
- Interactive health transition scatter plot
- Male-female infant mortality gap choropleth

## Data Sources

- World Bank, **World Development Indicators**, accessed 2026
- United Nations, **World Economic Situation and Prospects 2025**
- Natural Earth, Admin 0 Countries Dataset
- Gapminder Foundation visual development references

## Running the Dash App Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the combined dashboard app:

```bash
python app.py
```

Then open the local URL printed in the terminal, usually `http://127.0.0.1:8050`.

## Deployment Notes

The included `Procfile` is configured for Render:

```txt
web: gunicorn app:server
```

The static website can be hosted through GitHub Pages. The Dash app requires a Python server such as Render unless the interactive dashboard is exported or rewritten as static JavaScript/Plotly HTML.

## Static vs. Dash Visualizations

Not every visualization needs Render. Static Plotly exports, PNGs, and standalone HTML files can be embedded directly into the website. Dash is only necessary for visualizations that rely on live Python callbacks, server-side filtering, or dynamic app state.

## License and Credits

This website was created as coursework for George Mason University Korea. Template inspiration comes from the CDS 301 template website and the Nerfies project site. Licensed under Creative Commons Attribution-ShareAlike 4.0 International.
