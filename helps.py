import requests
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
import pandas as pd
import streamlit as st
import datetime
import math
import textwrap


def add_transit_times_to_schedule(
    df, ordered_spots, spots_info, transit_minutes_per_mile=30
):
    """
    Insert transit rows between spots showing walking distance and estimated walking time.
    Args:
        df (pd.DataFrame): Spot rows DataFrame without distance column.
        ordered_spots (list): Ordered list of spot names.
        spots_info (dict): Spot info dictionary with 'coords'.
        transit_minutes_per_mile (float): Minutes to walk 1 mile (as the crow flies).
    Returns:
        pd.DataFrame: Expanded DataFrame with transit rows inserted.
    """
    rows = []
    for i in range(len(df)):
        # Append the spot row
        rows.append(df.iloc[i].to_dict())
        # Add transit row if not last spot
        if i < len(df) - 1:
            # Calculate distance between current spot and next spot
            coord1 = spots_info[ordered_spots[i]]["coords"]
            coord2 = spots_info[ordered_spots[i + 1]]["coords"]
            dist = haversine_miles(coord1, coord2)
            transit_time = dist * transit_minutes_per_mile
            transit_row = {
                "Category": "walking",
                "Spot": f"Walk approx. {dist:.2f} miles",
                "Time (min)": f"{transit_time:.0f}",
                "Time Arriving": "",
                "Time Leaving": "",
            }

            rows.append(transit_row)
    expanded_df = pd.DataFrame(rows)
    return expanded_df

def haversine_miles(coord1, coord2):
    """
    Calculate the great-circle distance between two points on the earth (decimal degrees).
    Returns distance in miles.
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    # Convert decimal degrees to radians
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    radius_earth_miles = 3958.8  # Earth's radius in miles
    distance_miles = radius_earth_miles * c
    return distance_miles

def calculate_distances_between_spots(ordered_spots, spots_info):
    """
    Calculate distances in miles between each consecutive spot in ordered_spots.

    Args:
        ordered_spots (list): List of spot keys in the order you want to measure distances.
        spots_info (dict): Dictionary with spot info, where each spot has a 'coords' key as [lat, lon].

    Returns:
        list of floats: Distances in miles between consecutive spots.
                        The first distance is 0.0 (distance before the first spot).
    """

    distances = [0.0]  # No distance for the first spot
    for i in range(1, len(ordered_spots)):
        coord1 = spots_info[ordered_spots[i - 1]]["coords"]
        coord2 = spots_info[ordered_spots[i]]["coords"]
        dist = haversine_miles(coord1, coord2)
        distances.append(dist)
    return distances

def time_to_timedelta(t):
    """Convert datetime.time to datetime.timedelta"""
    return datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

def calculate_arrival_and_leaving_times(start_time, ordered_spots, spots_info):
    """
    Calculate arrival and leaving times for each spot in order.

    Args:
        start_time (datetime.time): Time when the schedule starts.
        ordered_spots (list): List of spot keys in order.
        spots_info (dict): Spot info dict, where each spot has a 'time' key (duration at spot),
                           duration can be datetime.time or number (minutes).

    Returns:
        tuple: (arrival_times, leaving_times)
            - arrival_times: list of datetime.time objects representing arrival times at each spot.
            - leaving_times: list of datetime.time objects representing leaving times from each spot.
    """

    base_date = datetime.date.today()
    current_dt = datetime.datetime.combine(base_date, start_time)
    arrival_times = []
    leaving_times = []
    for spot in ordered_spots:
        arrival_times.append(current_dt.time())
        # Get duration at spot
        spot_time = spots_info[spot].get("time")
        # Convert duration to timedelta
        if isinstance(spot_time, datetime.time):
            duration = time_to_timedelta(spot_time)
        elif isinstance(spot_time, (int, float)):
            duration = datetime.timedelta(minutes=spot_time)
        else:
            duration = datetime.timedelta()  # default zero if missing or invalid
        # Calculate leaving time for this spot
        current_dt += duration
        leaving_times.append(current_dt.time())
    return arrival_times, leaving_times


@st.cache_data
def get_osm_way_polygon(way_id: int) -> Polygon:
    """
    Fetch an OSM way by its ID and return its geometry as a Shapely Polygon.
    Parameters:
        way_id (int): The OSM way ID.

    Returns:
        shapely.geometry.Polygon: The polygon representing the way geometry.

    Raises:
        ValueError: If way or nodes are missing or polygon cannot be formed.
        requests.HTTPError: If HTTP request to OSM API fails.
    """

    url = f"https://api.openstreetmap.org/api/0.6/way/{way_id}/full"
    response = requests.get(url)
    response.raise_for_status()  # Raise error if request failed
    root = ET.fromstring(response.content)
    # Extract all nodes in the response
    nodes = {}
    for node in root.findall("node"):
        node_id = node.attrib["id"]
        lat = float(node.attrib["lat"])
        lon = float(node.attrib["lon"])
        nodes[node_id] = (lon, lat)  # Shapely expects (x, y) = (lon, lat)
    # Find the way element
    way = root.find("way")
    if way is None:
        raise ValueError(f"Way with id {way_id} not found in OSM data.")
    # Extract node references from way and get their coordinates
    way_node_coords = []
    for nd in way.findall("nd"):
        ref = nd.attrib["ref"]
        if ref not in nodes:
            raise ValueError(f"Node id {ref} referenced by way but not found in nodes.")
        way_node_coords.append(nodes[ref])
    # Ensure polygon is closed by repeating first coordinate if necessary
    if way_node_coords[0] != way_node_coords[-1]:
        way_node_coords.append(way_node_coords[0])
    polygon = Polygon(way_node_coords)
    if not polygon.is_valid:
        raise ValueError("Constructed polygon is not valid.")
    return polygon

def insert_line_breaks(text, max_chars=60):
    """
    Insert <br> tags into text every max_chars characters to force line breaks.
    """
    wrapped_lines = textwrap.wrap(text, width=max_chars)
    return "<br>".join(wrapped_lines)
