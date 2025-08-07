import folium
import yaml
from helps import insert_line_breaks, get_osm_way_polygon


def base_map():
    # Coordinates for Matera, Italy
    matera_coords = [40.6667, 16.6]
    matera_map = folium.Map(
        location=matera_coords,
        zoom_start=15,
        tiles="Cartodb Positron",
        font_size="0.5rem",
    )
    return matera_map

def add_to_map(info, color):
    temp_fg = folium.FeatureGroup("temp")
    for name, info in info.items():
        coords = info["coords"]
        desc = info["desc"]
        desc_wrapped = insert_line_breaks(desc, max_chars=60)
        tooltip_text = f"<b>{name}</b><br>{desc_wrapped}"
        folium.Circle(
            location=coords, radius=1, color=color, fill_color=color, fill_opacity=1
        ).add_to(temp_fg)
        folium.Circle(
            location=coords,
            radius=15,
            color=color,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(name, parse_html=True),
            tooltip=folium.Tooltip(tooltip_text, sticky=True),
        ).add_to(temp_fg)

    return temp_fg

def get_sasso():
    sasso_fg = folium.FeatureGroup("sasso")
    # old buildings preserved
    caveoso_id = 326515081
    caveoso_polygon = get_osm_way_polygon(caveoso_id)
    caveoso_coords = [(lat, lon) for lon, lat in caveoso_polygon.exterior.coords]
    # old buildings repurposed
    barisano_id = 326515348
    barisano_polygon = get_osm_way_polygon(barisano_id)
    barisano_coords = [(lat, lon) for lon, lat in barisano_polygon.exterior.coords]
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

    return sasso_fg


def get_spots():
    spots_fg = folium.FeatureGroup(name="spots")
    all_spots = {}
    def load_spots(file_path, color, category_label):
        with open(file_path, "r") as file:
            spots = yaml.safe_load(file)
        # Add category label to each spot
        for spot_key in spots:
            spots[spot_key]["category"] = category_label
        # Add markers to map
        marks = add_to_map(spots, color)
        marks.add_to(spots_fg)
        return spots

    # Load each category with label
    attractions = load_spots("spots/attraction.yaml", "blue", "attraction")
    church = load_spots("spots/church.yaml", "red", "church")
    bond = load_spots("spots/bond.yaml", "gray", "bond")
    viewpoint = load_spots("spots/viewpoint.yaml", "green", "viewpoint")
    food = load_spots("spots/food.yaml", "purple", "food")
    parking = load_spots("spots/parking.yaml", "lightgreen", "parking")

    # Combine all spots into one dictionary
    all_spots.update(attractions)
    all_spots.update(church)
    all_spots.update(bond)
    all_spots.update(viewpoint)
    all_spots.update(food)
    all_spots.update(parking)

    return spots_fg, all_spots
