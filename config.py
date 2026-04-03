# ─────────────────────────────────────────────
#  config.py  –  Flight Tracker Configuration
# ─────────────────────────────────────────────

# ── Location ──────────────────────────────────
# Bounding box around Lynnwood, WA (adjust to taste)
# Format: (lat_min, lon_min, lat_max, lon_max)
BOUNDING_BOX = (47.6, -122.5, 48.0, -122.0)

# ── Refresh ───────────────────────────────────
REFRESH_INTERVAL_SECONDS = 60   # how often to poll OpenSky
MAX_AIRCRAFT_SHOWN = 3          # rows visible on the display

# ── OpenSky API ───────────────────────────────
# Leave as None to use the unauthenticated endpoint (rate-limited to ~100 req/day)
# Register free at https://opensky-network.org/ for a higher quota
OPENSKY_USER = None
OPENSKY_PASS = None

# ── Display ───────────────────────────────────
# Common Waveshare sizes – uncomment the one you own:
# DISPLAY_MODEL = "epd2in13_V4"   # 2.13"  250×122
# DISPLAY_MODEL = "epd2in9_V2"    # 2.9"   296×128
DISPLAY_MODEL = "epd4in2"         # 4.2"   400×300  ← most common for this project
# DISPLAY_MODEL = "epd7in5_V2"    # 7.5"   800×480

# Set these to match your chosen display's native resolution
DISPLAY_WIDTH  = 400
DISPLAY_HEIGHT = 300

# ── Fonts ─────────────────────────────────────
# Pillow will fall back to the default bitmap font if these paths don't exist.
# Install: sudo apt install fonts-dejavu-core
FONT_PATH       = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_PATH_BOLD  = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

FONT_SIZE_HEADER = 14
FONT_SIZE_ROW    = 11
FONT_SIZE_FOOTER = 9

# ── Airline lookup (ICAO prefix → friendly name) ──────────────────────────────
# Extend this dict with any callsigns you see locally.
AIRLINE_MAP = {
    "AAL": "American",
    "ACA": "Air Canada",
    "AFR": "Air France",
    "AJX": "Air Japan",
    "AKL": "Alaska Cargo",
    "ALK": "SriLankan",
    "AMX": "Aeromexico",
    "ANZ": "Air NZ",
    "ASA": "Alaska",
    "ATC": "Air Tanzania",
    "AUA": "Austrian",
    "BAW": "British",
    "CAL": "China Airlines",
    "CCA": "Air China",
    "CES": "China Eastern",
    "CSN": "China Southern",
    "DAL": "Delta",
    "DLH": "Lufthansa",
    "EDV": "Endeavor",
    "EIN": "Aer Lingus",
    "EJA": "NetJets",
    "ELY": "El Al",
    "EVA": "EVA Air",
    "FDX": "FedEx",
    "FFT": "Frontier",
    "FIN": "Finnair",
    "GWA": "Germanwings",
    "HAL": "Hawaiian",
    "JAL": "Japan Air",
    "JBU": "JetBlue",
    "JZA": "Jazz",
    "KAL": "Korean Air",
    "KLM": "KLM",
    "LAN": "LATAM",
    "LOG": "Loganair",
    "LXJ": "Flexjet",
    "MAS": "Malaysia",
    "NKS": "Spirit",
    "PAC": "Polar Air",
    "QFA": "Qantas",
    "QXE": "Horizon",
    "RPA": "Republic",
    "SAS": "Scandinavian",
    "SCX": "Sun Country",
    "SIA": "Singapore",
    "SKW": "SkyWest",
    "SWA": "Southwest",
    "SWR": "Swiss",
    "THY": "Turkish",
    "UAL": "United",
    "UPS": "UPS",
    "VRD": "Virgin",
    "WJA": "WestJet",
    "WN":  "Southwest",
}
