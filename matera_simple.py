from maps import get_spots, get_sasso
from streamlit_folium import st_folium
import streamlit as st
import folium

st.set_page_config(
    page_title="Matera Map",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Create a simple map showing all spots with their names
# Use OpenStreetMap tiles which might work better
matera_coords = [40.6667, 16.6]
m = folium.Map(
    location=matera_coords,
    zoom_start=15,
    tiles="OpenStreetMap",
)

# Get sassi polygons from the same source as matera.py, with fallback
try:
    sassos = get_sasso()
    sassos.add_to(m)
except Exception as e:
    # Fallback to hardcoded coordinates if OSM API fails
    print(f"Could not fetch OSM data ({e}), using fallback coordinates")
    sasso_fg = folium.FeatureGroup("sasso")
    
    # Use the same hardcoded coordinates as before (these are reasonable approximations)
    # Caveoso polygon (Old Old sassi)
    caveoso_coords = [
        [40.6650, 16.6090],
        [40.6645, 16.6110],
        [40.6640, 16.6125],
        [40.6642, 16.6135],
        [40.6648, 16.6140],
        [40.6655, 16.6130],
        [40.6660, 16.6115],
        [40.6655, 16.6095],
        [40.6650, 16.6090]
    ]

    # Barisano polygon (Modern Old sassi) 
    barisano_coords = [
        [40.6660, 16.6060],
        [40.6665, 16.6080],
        [40.6670, 16.6095],
        [40.6675, 16.6105],
        [40.6672, 16.6115],
        [40.6668, 16.6120],
        [40.6662, 16.6110],
        [40.6658, 16.6095],
        [40.6655, 16.6080],
        [40.6660, 16.6060]
    ]

    folium.Polygon(
        locations=caveoso_coords,
        tooltip="Caveoso (Old Old)",
        color="brown",
        fill_color="brown",
        fill_opacity=0.25,
        fill=True,
    ).add_to(sasso_fg)

    folium.Polygon(
        locations=barisano_coords,
        tooltip="Barisano (Modern Old)",
        color="yellow", 
        fill_color="yellow",
        fill_opacity=0.25,
        fill=True,
    ).add_to(sasso_fg)
    
    sasso_fg.add_to(m)

# Add all spots to the map with names displayed
spots_map, spots_info = get_spots()
spots_map.add_to(m)

# Add location names as visible text on the map
for spot_name, spot_data in spots_info.items():
    coords = spot_data["coords"]
    folium.map.Marker(
        coords,
        icon=folium.DivIcon(
            html=f'<div style="font-size: 12px; font-weight: bold; color: black; background-color: white; padding: 2px; border-radius: 3px; border: 1px solid black;">{spot_name}</div>',
            class_name="spot-name-label"
        )
    ).add_to(m)

# Display the map
st_folium(
    m,
    height=600,
    use_container_width=True,
)
