"""
app/utils/geo.py

Small geographic utilities. No external dependency — plain haversine
great-circle distance, sufficient for regional (district/state scale)
proximity comparisons used across the platform's prioritisation logic.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

_EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/long points."""
    lat1_r, lon1_r, lat2_r, lon2_r = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * asin(sqrt(a))
