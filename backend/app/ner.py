from __future__ import annotations

# ---------------------------------------------------------------------------
# North Eastern Region (NER) - India geographic configuration.
# Bounds are administrative bounding boxes used to keep the dashboard NER-focused.
# ---------------------------------------------------------------------------
NER_BOUNDS = {
    "min_latitude": 21.5,
    "max_latitude": 29.5,
    "min_longitude": 88.0,
    "max_longitude": 98.0,
}

NER_STATE_BOUNDS = [
    {"state": "Arunachal Pradesh", "min_latitude": 26.6, "max_latitude": 29.5, "min_longitude": 91.4, "max_longitude": 97.4},
    {"state": "Assam", "min_latitude": 24.1, "max_latitude": 28.0, "min_longitude": 89.6, "max_longitude": 96.2},
    {"state": "Manipur", "min_latitude": 23.7, "max_latitude": 25.7, "min_longitude": 93.0, "max_longitude": 94.8},
    {"state": "Meghalaya", "min_latitude": 24.9, "max_latitude": 26.2, "min_longitude": 89.7, "max_longitude": 92.8},
    {"state": "Mizoram", "min_latitude": 21.9, "max_latitude": 24.5, "min_longitude": 92.2, "max_longitude": 93.5},
    {"state": "Nagaland", "min_latitude": 25.2, "max_latitude": 27.1, "min_longitude": 93.2, "max_longitude": 95.2},
    {"state": "Sikkim", "min_latitude": 27.0, "max_latitude": 28.2, "min_longitude": 88.0, "max_longitude": 88.9},
    {"state": "Tripura", "min_latitude": 22.9, "max_latitude": 24.5, "min_longitude": 91.1, "max_longitude": 92.4},
]


def state_for(latitude: float, longitude: float) -> str | None:
    """Return the NER state containing a coordinate, if any."""
    for sb in NER_STATE_BOUNDS:
        if (sb["min_latitude"] <= latitude <= sb["max_latitude"]
                and sb["min_longitude"] <= longitude <= sb["max_longitude"]):
            return sb["state"]
    return None


def in_ner(latitude: float, longitude: float) -> bool:
    b = NER_BOUNDS
    return b["min_latitude"] <= latitude <= b["max_latitude"] and b["min_longitude"] <= longitude <= b["max_longitude"]


# ---------------------------------------------------------------------------
# Hotspot candidate grid: representative real NER towns / landslide-prone
# corridors. Static administrative names are facts, not live sensor data.
# Only the risk evaluation (weather/terrain/OSM/model) is fetched live.
# ---------------------------------------------------------------------------
HOTSPOT_CANDIDATES = [
    # Sikkim
    {"name": "Gangtok", "district": "East Sikkim", "state": "Sikkim", "lat": 27.3314, "lon": 88.6139},
    {"name": "Namchi", "district": "Namchi", "state": "Sikkim", "lat": 27.1655, "lon": 88.3630},
    {"name": "Mangan", "district": "Mangan", "state": "Sikkim", "lat": 27.5195, "lon": 88.5343},
    {"name": "Gyalshing", "district": "Gyalshing", "state": "Sikkim", "lat": 27.2881, "lon": 88.2534},
    {"name": "Rongli", "district": "Pakyong", "state": "Sikkim", "lat": 27.1874, "lon": 88.6986},
    # Meghalaya
    {"name": "Shillong", "district": "East Khasi Hills", "state": "Meghalaya", "lat": 25.5788, "lon": 91.8933},
    {"name": "Cherrapunji", "district": "East Khasi Hills", "state": "Meghalaya", "lat": 25.2792, "lon": 91.7104},
    {"name": "Jowai", "district": "West Jaintia Hills", "state": "Meghalaya", "lat": 25.4509, "lon": 92.2037},
    {"name": "Nongstoin", "district": "West Khasi Hills", "state": "Meghalaya", "lat": 25.5200, "lon": 91.2620},
    {"name": "Tura", "district": "West Garo Hills", "state": "Meghalaya", "lat": 25.5155, "lon": 90.2023},
    # Arunachal Pradesh
    {"name": "Itanagar", "district": "Papum Pare", "state": "Arunachal Pradesh", "lat": 27.1025, "lon": 93.6264},
    {"name": "Ziro", "district": "Lower Subansiri", "state": "Arunachal Pradesh", "lat": 27.5500, "lon": 93.8160},
    {"name": "Bomdila", "district": "West Kameng", "state": "Arunachal Pradesh", "lat": 27.2670, "lon": 92.4220},
    {"name": "Along", "district": "West Siang", "state": "Arunachal Pradesh", "lat": 28.1695, "lon": 94.8000},
    {"name": "Tawang", "district": "Tawang", "state": "Arunachal Pradesh", "lat": 27.5863, "lon": 91.8595},
    # Assam
    {"name": "Guwahati", "district": "Kamrup Metropolitan", "state": "Assam", "lat": 26.1445, "lon": 91.7362},
    {"name": "Silchar", "district": "Cachar", "state": "Assam", "lat": 24.8300, "lon": 92.7979},
    {"name": "Diphu", "district": "Karbi Anglong", "state": "Assam", "lat": 25.8420, "lon": 93.4300},
    {"name": "Lumding", "district": "Hojai", "state": "Assam", "lat": 25.7480, "lon": 93.1700},
    {"name": "Haflong", "district": "Dima Hasao", "state": "Assam", "lat": 25.1600, "lon": 93.0200},
    # Mizoram
    {"name": "Aizawl", "district": "Aizawl", "state": "Mizoram", "lat": 23.7271, "lon": 92.7176},
    {"name": "Lunglei", "district": "Lunglei", "state": "Mizoram", "lat": 22.8922, "lon": 92.7382},
    {"name": "Champhai", "district": "Champhai", "state": "Mizoram", "lat": 23.4498, "lon": 93.3310},
    {"name": "Serchhip", "district": "Serchhip", "state": "Mizoram", "lat": 23.3030, "lon": 92.8470},
    {"name": "Kolasib", "district": "Kolasib", "state": "Mizoram", "lat": 24.2300, "lon": 92.6800},
    # Nagaland
    {"name": "Kohima", "district": "Kohima", "state": "Nagaland", "lat": 25.6751, "lon": 94.1086},
    {"name": "Dimapur", "district": "Dimapur", "state": "Nagaland", "lat": 25.9090, "lon": 93.7260},
    {"name": "Mokokchung", "district": "Mokokchung", "state": "Nagaland", "lat": 26.3240, "lon": 94.5190},
    {"name": "Wokha", "district": "Wokha", "state": "Nagaland", "lat": 26.0964, "lon": 94.2616},
    {"name": "Mon", "district": "Mon", "state": "Nagaland", "lat": 26.7240, "lon": 95.0270},
    # Manipur
    {"name": "Imphal", "district": "Imphal West", "state": "Manipur", "lat": 24.8170, "lon": 93.9368},
    {"name": "Ukhrul", "district": "Ukhrul", "state": "Manipur", "lat": 25.1017, "lon": 94.3606},
    {"name": "Churachandpur", "district": "Churachandpur", "state": "Manipur", "lat": 24.3353, "lon": 93.6895},
    {"name": "Tamenglong", "district": "Tamenglong", "state": "Manipur", "lat": 24.9950, "lon": 93.4870},
    {"name": "Senapati", "district": "Senapati", "state": "Manipur", "lat": 25.2670, "lon": 94.0270},
    # Tripura
    {"name": "Agartala", "district": "West Tripura", "state": "Tripura", "lat": 23.8315, "lon": 91.2868},
    {"name": "Udaipur", "district": "Gomati", "state": "Tripura", "lat": 23.5332, "lon": 91.4794},
    {"name": "Kailashahar", "district": "Unakoti", "state": "Tripura", "lat": 24.3290, "lon": 92.0470},
    {"name": "Ambassa", "district": "Dhalai", "state": "Tripura", "lat": 23.9250, "lon": 91.8520},
    {"name": "Sabroom", "district": "South Tripura", "state": "Tripura", "lat": 23.0000, "lon": 91.7200},
]