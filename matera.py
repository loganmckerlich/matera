from map import base_map, get_sasso, get_spots
from helps import *
from streamlit_folium import st_folium
import streamlit as st
from streamlit_sortables import sort_items
import folium
import pandas as pd
import datetime as dt
st.set_page_config(
    page_title="My App",
    layout="wide",  # Use the full width of the browser window
    initial_sidebar_state="collapsed",  # Optional: collapse sidebar by default
)
# Create the sortable list (vertical by default)
# passeggiata this is basically a tradition
# where people just walk around at end of day
m = base_map()
sassos = get_sasso()
sassos.add_to(m)
spots_map, spots_info = get_spots()
spots_map.add_to(m)
spot_names = list(spots_info.keys())
spot_names = [str(v["category"].title()) + ": " + str(k)
              for k, v in spots_info.items()]
sort_info = [
    {"header": "Discard", "items": spot_names},
    {"header": "Visit", "items": []},
]

a, b = st.columns([0.25, 0.75])

with a:
    new_order = sort_items(
        sort_info,
        direction="vertical",
        multi_containers=True)
    ordered_spot_names = [x.split(": ")[-1] for x in new_order[1]["items"]]
    route_coords = [spots_info[spot]["coords"] for spot in ordered_spot_names]
with b:
    route_fg = folium.FeatureGroup("route")
    if len(route_coords) > 1:
        route = folium.PolyLine(
            locations=route_coords,
            color="blue",
            weight=2,
            opacity=0.7,
            tooltip="Route").add_to(route_fg)
    _ = st_folium(
        m,
        feature_group_to_add=route_fg,
        height=500,
        use_container_width=True,
    )

start_time = st.time_input("Start Time", value=dt.time(9, 00))
arrival_times, leaving_times = calculate_arrival_and_leaving_times(
    start_time, ordered_spot_names, spots_info
)

df = pd.DataFrame(
    {
        "Category": [
            spots_info[spot].get("category", 0) for spot in ordered_spot_names
        ],
        "Spot": ordered_spot_names,
        "Time (min)": [spots_info[spot].get("time", 0) for spot in ordered_spot_names],
        "Time Arriving": [t.strftime("%H:%M:%S") for t in arrival_times],
        "Time Leaving": [t.strftime("%H:%M:%S") for t in leaving_times],
        # 'Distance to Next Spot (Bird Miles)': calculate_distances_between_spots(ordered_spot_names, spots_info)
    }
)

if len(df) > 0:
    transit_df = add_transit_times_to_schedule(
        df, ordered_spot_names, spots_info, transit_minutes_per_mile=60
    )
    st.dataframe(transit_df)
