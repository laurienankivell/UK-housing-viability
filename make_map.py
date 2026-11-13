# Builds index.html (the GitHub Pages map) from sites.csv.
# To add a developer: add rows to sites.csv with their name in the "layer" column,
# then run:  python make_map.py
# Every distinct "layer" becomes its own tickbox on the map.

import json
import altair as alt
import folium
import pandas as pd

sites = pd.read_csv("sites.csv")

# One colour per layer, in order of first appearance. 
COLOURS = ["#e74c3c", "#2a78d6", "#1baf7a", "#eda100", "#4a3aa7"]


def popup_chart(row, colour):
    """A small slope chart: Target -> Promised (if known) -> Delivered/Approved."""
    stages = ["Target"]
    values = [row["target_pct"]]
    if pd.notna(row["promised_pct"]):
        stages.append("Promised")
        values.append(row["promised_pct"])
    stages.append(row["actual_stage"])
    values.append(row["actual_pct"])

    subtitle = ""
    if pd.notna(row["social_rent_pct"]):
        subtitle = f"{row['social_rent_pct']:.0f}% social rent, {row['intermediate_pct']:.0f}% shared ownership etc."

    chart = alt.Chart(pd.DataFrame({"Stage": stages, "Percentage": values})).mark_line(point=True, size=4).encode(
        x=alt.X("Stage:N", sort=stages, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Percentage:Q", scale=alt.Scale(domain=[0, 60]), title="Affordable %"),
        color=alt.value(colour),
    ).properties(title=alt.Title(row["name"], subtitle=subtitle), width=180, height=150
    ).configure_view(stroke=None).configure_axis(grid=False)

    popup = folium.Popup(max_width=300)
    folium.features.VegaLite(json.loads(chart.to_json()), height=220, width=250).add_to(popup)
    return popup


# The map
m = folium.Map(location=[52.5, -1.5], zoom_start=6, tiles=None)
m.default_js = [js for js in m.default_js if js[0] in ("leaflet", "jquery")]  # jquery: needed by the popups
m.default_css = [css for css in m.default_css if css[0] == "leaflet_css"]
folium.TileLayer("OpenStreetMap", control=False).add_to(m)  # CartoDB tiles now need an API key

for i, (layer_name, rows) in enumerate(sites.groupby("layer", sort=False)):
    colour = COLOURS[i % len(COLOURS)]
    layer = folium.FeatureGroup(name=layer_name).add_to(m)
    for _, row in rows.iterrows():
        hover = f"<b>{row['name']}</b><br>Target {row['target_pct']:.0f}%, {row['actual_stage'].lower()} {row['actual_pct']:.0f}%"
        if isinstance(row["note"], str) and row["note"]:
            hover += f"<br>{row['note']}"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]], radius=8, color="white", weight=1,
            fill=True, fill_color=colour, fill_opacity=0.85,
            tooltip=hover, popup=popup_chart(row, colour),
        ).add_to(layer)

folium.LayerControl(collapsed=False).add_to(m)
m.save("index.html")
print("Saved index.html")
