import math


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 0)


def policy_distance(travel: dict, policy: dict) -> float | None:
    """Return the distance on the configured basis only; never mixes radius and road distance."""
    key = "driving_distance_km" if policy.get("basis") == "driving" else "geo_distance_km"
    return (travel or {}).get(key)
