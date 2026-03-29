"""
renderer.py  –  Draw flight data onto a Pillow Image for e-ink output.

Layout (400×300 example):
  ┌──────────────────────────────────┐
  │  ✈ FLIGHT TRACKER  HH:MM        │  ← header bar (18 px)
  ├──────────────────────────────────┤
  │  CALL     AIRLINE   ALT   SPD PH │  ← column headers (12 px)
  ├──────────────────────────────────┤
  │  ASA123   Alaska  34000  420 CRZ │  ← data rows
  │  DAL456   Delta   28500  390 DSC │
  │  UAL789   United  12000  280 CLB │
  │  N12345   ——      ——     ——  GND │
  │  ...                             │
  ├──────────────────────────────────┤
  │  5 aircraft  · Lynnwood, WA      │  ← footer (10 px)
  └──────────────────────────────────┘
"""

import datetime
from PIL import Image, ImageDraw, ImageFont

import config
from fetcher import Aircraft


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size)
    except (IOError, OSError):
        return ImageFont.load_default()


def _ft(val, fmt="{}", fallback="----") -> str:
    return fmt.format(val) if val is not None else fallback


# ── Main renderer ─────────────────────────────────────────────────────────────

class DisplayRenderer:
    """Generates a 1-bit Pillow Image ready for transfer to the e-ink panel."""

    W = config.DISPLAY_WIDTH
    H = config.DISPLAY_HEIGHT

    # Column x-positions (tune to your display width)
    COL_CALL    = 2
    COL_AIRLINE = 68
    COL_DIR     = 148
    COL_ALT     = 162
    COL_SPD     = 210
    COL_PHASE   = 252

    def __init__(self):
        self.font_h  = _load_font(config.FONT_PATH_BOLD, config.FONT_SIZE_HEADER)
        self.font_r  = _load_font(config.FONT_PATH,      config.FONT_SIZE_ROW)
        self.font_rb = _load_font(config.FONT_PATH_BOLD, config.FONT_SIZE_ROW)
        self.font_f  = _load_font(config.FONT_PATH,      config.FONT_SIZE_FOOTER)

    # ── Layout constants ──────────────────────────────────────────────────────

    @property
    def header_h(self) -> int:
        return config.FONT_SIZE_HEADER + 6

    @property
    def col_header_h(self) -> int:
        return config.FONT_SIZE_ROW + 4

    @property
    def row_h(self) -> int:
        return config.FONT_SIZE_ROW + 5

    @property
    def footer_h(self) -> int:
        return config.FONT_SIZE_FOOTER + 4

    # ── Draw helpers ──────────────────────────────────────────────────────────

    def _hline(self, draw: ImageDraw.Draw, y: int):
        draw.line([(0, y), (self.W - 1, y)], fill=0, width=1)

    def _text(self, draw, pos, txt, font, fill=0):
        draw.text(pos, txt, font=font, fill=fill)

    # ── Public API ────────────────────────────────────────────────────────────

    def render(self, aircraft: list[Aircraft]) -> Image.Image:
        """Return a W×H 1-bit Image with the flight table."""
        img  = Image.new("1", (self.W, self.H), 255)   # white background
        draw = ImageDraw.Draw(img)

        y = 0

        # ── Header ────────────────────────────────────────────────────────────
        now = datetime.datetime.now().strftime("%H:%M")
        draw.rectangle([0, 0, self.W, self.header_h], fill=0)  # black bar
        self._text(draw, (3, 2), "\u2708 FLIGHT TRACKER", self.font_h, fill=255)
        # Right-align the time
        try:
            tw = draw.textlength(now, font=self.font_h)
        except AttributeError:
            tw = len(now) * 8
        self._text(draw, (self.W - int(tw) - 3, 2), now, self.font_h, fill=255)

        y = self.header_h + 1

        # ── Column headers ────────────────────────────────────────────────────
        headers = [
            (self.COL_CALL,    "CALL"),
            (self.COL_AIRLINE, "AIRLINE"),
            (self.COL_ALT,     "ALT ft"),
            (self.COL_SPD,     "KTS"),
            (self.COL_PHASE,   "PH"),
        ]
        for x, label in headers:
            self._text(draw, (x, y), label, self.font_rb)

        y += self.col_header_h
        self._hline(draw, y)
        y += 2

        # ── Data rows ─────────────────────────────────────────────────────────
        shown = aircraft[:config.MAX_AIRCRAFT_SHOWN]

        for i, ac in enumerate(shown):
            # Alternate very light shading on every other row using a dotted line
            if i % 2 == 1:
                for px in range(0, self.W, 4):
                    draw.point((px, y + self.row_h // 2), fill=0)

            alt_str = _ft(ac.altitude_ft, "{:,}")
            spd_str = _ft(ac.speed_kts,   "{}")

            self._text(draw, (self.COL_CALL,    y), ac.callsign_clean[:7], self.font_rb)
            self._text(draw, (self.COL_AIRLINE, y), ac.airline[:9],        self.font_r)
            self._text(draw, (self.COL_DIR,     y), ac.direction_arrow,    self.font_r)
            self._text(draw, (self.COL_ALT,     y), alt_str,               self.font_r)
            self._text(draw, (self.COL_SPD,     y), spd_str,               self.font_r)
            self._text(draw, (self.COL_PHASE,   y), ac.phase,              self.font_rb)

            y += self.row_h

        # Fill empty rows with dashes
        for _ in range(config.MAX_AIRCRAFT_SHOWN - len(shown)):
            self._text(draw, (self.COL_CALL, y), "  ——  no traffic  ——", self.font_r)
            y += self.row_h

        # ── Footer ────────────────────────────────────────────────────────────
        footer_y = self.H - self.footer_h
        self._hline(draw, footer_y - 2)
        n = len(aircraft)
        footer = f"{n} aircraft in range  \u00b7  bbox {config.BOUNDING_BOX[0]}\u00b0N {abs(config.BOUNDING_BOX[1])}\u00b0W"
        self._text(draw, (2, footer_y), footer, self.font_f)

        return img


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    from fetcher import Aircraft
    dummy = [
        Aircraft("a1b2c3","ASA123 ","US",47.82,-122.31,10363,215,274,2.1,False,"1234"),
        Aircraft("d4e5f6","DAL456 ","US",47.75,-122.20,8687, 200,180,-3.0,False,"4567"),
        Aircraft("g7h8i9","UAL789 ","US",47.90,-122.40,3658, 150,310,5.5,False,"7890"),
        Aircraft("j1k2l3","N12345 ","US",47.85,-122.35,None, None,None,None,True,"2000"),
    ]
    rdr = DisplayRenderer()
    img = rdr.render(dummy)
    img.save("/tmp/test_render.png")
    print("Saved test image to /tmp/test_render.png")
