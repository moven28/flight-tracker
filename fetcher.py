"""
fetcher.py  –  Pull live flight states from the OpenSky Network REST API.

OpenSky free tier: ~100 requests/day unauthenticated, ~4 req/s authenticated.
API docs: https://openskynetwork.github.io/opensky-api/rest.html
"""

import time
import requests
from dataclasses import dataclass, field
from typing import Optional

import config

# OpenSky state vector field indices
_IDX = {
    "icao24":      0,
    "callsign":    1,
    "origin":      2,
    "time_pos":    3,
    "last_contact":4,
    "lon":         5,
    "lat":         6,
    "baro_alt":    7,
    "on_ground":   8,
    "velocity":    9,
    "heading":    10,
    "vert_rate":  11,
    "sensors":    12,
    "geo_alt":    13,
    "squawk":     14,
    "spi":        15,
    "pos_source": 16,
}

OPENSKY_URL      = "https://opensky-network.org/api/states/all"
OPENSKY_META_URL = "https://opensky-network.org/api/metadata/aircraft/icao/{icao24}"

# Simple in-memory cache so we don't re-fetch the same aircraft type repeatedly
_type_cache: dict[str, str] = {}


@dataclass
class Aircraft:
    icao24:       str
    callsign:     str
    origin:       str
    lat:          Optional[float]
    lon:          Optional[float]
    altitude:     Optional[float]   # metres
    velocity:     Optional[float]   # m/s
    heading:      Optional[float]   # degrees
    vert_rate:    Optional[float]   # m/s  (+climb / -descend)
    on_ground:    bool
    squawk:       str
    aircraft_type: str = "——"       # e.g. "B738", "A320", fetched separately

    # ── Derived helpers ─────────────────────────────────────────────────────

    @property
    def callsign_clean(self) -> str:
        return self.callsign.strip() if self.callsign else "??????"

    @property
    def airline(self) -> str:
        """Return friendly airline name from the ICAO prefix, or the raw prefix."""
        cs = self.callsign_clean
        if len(cs) >= 3:
            prefix3 = cs[:3].upper()
            if prefix3 in config.AIRLINE_MAP:
                return config.AIRLINE_MAP[prefix3]
            prefix2 = cs[:2].upper()
            if prefix2 in config.AIRLINE_MAP:
                return config.AIRLINE_MAP[prefix2]
        return cs[:6] if cs else "?"

    @property
    def altitude_ft(self) -> Optional[int]:
        if self.altitude is None:
            return None
        return int(self.altitude * 3.28084)

    @property
    def speed_kts(self) -> Optional[int]:
        if self.velocity is None:
            return None
        return int(self.velocity * 1.94384)

    @property
    def direction_arrow(self) -> str:
        """Unicode arrow roughly matching heading (8 compass points)."""
        if self.heading is None:
            return "·"
        arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
        idx = int((self.heading + 22.5) / 45) % 8
        return arrows[idx]

    @property
    def phase(self) -> str:
        """Simple phase-of-flight label."""
        if self.on_ground:
            return "GND"
        vr = self.vert_rate or 0
        if vr > 2:
            return "CLB"
        if vr < -2:
            return "DSC"
        return "CRZ"


def _parse_state(sv: list) -> Optional[Aircraft]:
    """Convert a raw OpenSky state vector into an Aircraft object."""
    try:
        return Aircraft(
            icao24    = sv[_IDX["icao24"]]    or "",
            callsign  = sv[_IDX["callsign"]]  or "",
            origin    = sv[_IDX["origin"]]    or "??",
            lat       = sv[_IDX["lat"]],
            lon       = sv[_IDX["lon"]],
            altitude  = sv[_IDX["baro_alt"]],
            velocity  = sv[_IDX["velocity"]],
            heading   = sv[_IDX["heading"]],
            vert_rate = sv[_IDX["vert_rate"]],
            on_ground = bool(sv[_IDX["on_ground"]]),
            squawk    = sv[_IDX["squawk"]] or "----",
        )
    except Exception:
        return None


def fetch_aircraft_type(icao24: str, auth=None) -> str:
    """
    Look up the aircraft type designator (e.g. B738, A320) from the
    OpenSky metadata endpoint. Results are cached in memory.
    """
    if not icao24:
        return "——"
    key = icao24.lower()
    if key in _type_cache:
        return _type_cache[key]
    try:
        url  = OPENSKY_META_URL.format(icao24=key)
        resp = requests.get(url, auth=auth, timeout=10)
        if resp.status_code == 200:
            data  = resp.json()
            # typecode is the ICAO aircraft type designator e.g. "B738"
            atype = data.get("typecode") or data.get("model") or "——"
            atype = atype.strip()[:6] or "——"
        else:
            atype = "——"
    except Exception:
        atype = "——"
    _type_cache[key] = atype
    return atype


def fetch_aircraft() -> list[Aircraft]:
    """
    Query OpenSky for the current bounding box and return a sorted list
    of Aircraft objects (airborne first, then by altitude descending).
    Also fetches aircraft type for each result.
    """
    lat_min, lon_min, lat_max, lon_max = config.BOUNDING_BOX
    params = {
        "lamin": lat_min,
        "lomin": lon_min,
        "lamax": lat_max,
        "lomax": lon_max,
    }

    auth = None
    if config.OPENSKY_USER and config.OPENSKY_PASS:
        auth = (config.OPENSKY_USER, config.OPENSKY_PASS)

    try:
        resp = requests.get(
            OPENSKY_URL,
            params=params,
            auth=auth,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        print(f"[fetcher] API error: {exc}")
        return []

    states = data.get("states") or []
    aircraft = [a for sv in states if (a := _parse_state(sv)) is not None]

    # Sort: airborne first, then highest altitude
    aircraft.sort(key=lambda a: (a.on_ground, -(a.altitude or 0)))

    # Only fetch type metadata for the top N aircraft we'll actually display
    # to avoid hammering the API with requests for every aircraft in range
    for ac in aircraft[:config.MAX_AIRCRAFT_SHOWN]:
        ac.aircraft_type = fetch_aircraft_type(ac.icao24, auth=auth)

    return aircraft
