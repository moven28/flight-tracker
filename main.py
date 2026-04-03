#!/usr/bin/env python3
"""
main.py  –  Flight Tracker for Raspberry Pi Zero W + Waveshare E-Ink display.

Usage:
    python3 main.py            # normal run
    python3 main.py --test     # render once to /tmp/test_render.png, no e-ink needed
    python3 main.py --demo     # show dummy data (no API call)

Dependencies:
    pip install requests Pillow RPi.GPIO spidev          # for Pi + real display
    pip install requests Pillow                          # for --test mode only

Waveshare library:
    git clone https://github.com/waveshare/e-Paper
    cp -r e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd ./waveshare_epd
"""

import sys
import time
import signal
import logging
import argparse

import config
from fetcher import fetch_aircraft, Aircraft
from renderer import DisplayRenderer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("tracker")


# ── E-Ink driver wrapper ───────────────────────────────────────────────────────

class EInkDisplay:
    """Thin wrapper around a Waveshare EPD driver."""

    def __init__(self):
        try:
            import importlib
            epd_mod = importlib.import_module(f"waveshare_epd.{config.DISPLAY_MODEL}")
            self.epd = epd_mod.EPD()
            self.epd.init()
            self.epd.Clear()
            self._real = True
            log.info("E-ink display initialised (%s).", config.DISPLAY_MODEL)
        except ImportError:
            log.warning("waveshare_epd not found – running in headless mode.")
            self.epd = None
            self._real = False

    def show(self, img):
        if self._real and self.epd is not None:
            self.epd.display(self.epd.getbuffer(img))
        else:
            # Headless: save to file for inspection
            out = "/tmp/flight_tracker_latest.png"
            img.save(out)
            log.info("Headless mode: image saved to %s", out)

    def sleep(self):
        if self._real and self.epd is not None:
            try:
                self.epd.sleep()
            except Exception:
                pass

    def cleanup(self):
        if self._real:
            try:
                from waveshare_epd import epdconfig
                epdconfig.module_exit(cleanup=True)
            except Exception:
                pass


# ── Demo data ─────────────────────────────────────────────────────────────────

def _demo_aircraft() -> list[Aircraft]:
    return [
        Aircraft("a1b2c3", "ASA123 ", "US", 47.82, -122.31, 10363, 215, 274,  2.1, False, "1234", "B739"),
        Aircraft("d4e5f6", "DAL456 ", "US", 47.75, -122.20,  8687, 200, 180, -3.0, False, "4567", "A321"),
        Aircraft("g7h8i9", "UAL789 ", "US", 47.90, -122.40,  3658, 150, 310,  5.5, False, "7890", "B738"),
    ]


# ── Signal handling ───────────────────────────────────────────────────────────

_running = True

def _shutdown(sig, frame):
    global _running
    log.info("Shutdown signal received.")
    _running = False

signal.signal(signal.SIGINT,  _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="E-Ink Flight Tracker")
    parser.add_argument("--test", action="store_true",
                        help="Fetch once, save PNG, exit (no e-ink required)")
    parser.add_argument("--demo", action="store_true",
                        help="Use dummy data – no API call")
    args = parser.parse_args()

    renderer = DisplayRenderer()

    # ── Single-shot modes ──────────────────────────────────────────────────────
    if args.demo or args.test:
        aircraft = _demo_aircraft() if args.demo else fetch_aircraft()
        img = renderer.render(aircraft)
        out = "/tmp/flight_tracker_test.png"
        img.save(out)
        log.info("Saved to %s  (%d aircraft)", out, len(aircraft))
        return

    # ── Continuous loop ────────────────────────────────────────────────────────
    display = EInkDisplay()

    try:
        while _running:
            log.info("Fetching aircraft…")
            aircraft = fetch_aircraft()
            log.info("  → %d aircraft in bounding box.", len(aircraft))

            img = renderer.render(aircraft)
            display.show(img)

            # E-ink panels degrade with rapid refreshes – sleep the panel between
            # updates to reduce ghosting and extend panel life.
            display.sleep()

            # Wait for the next poll interval (check _running every second)
            for _ in range(config.REFRESH_INTERVAL_SECONDS):
                if not _running:
                    break
                time.sleep(1)

            # Wake the panel before the next refresh
            if _running and display._real and display.epd:
                display.epd.init()

    finally:
        display.cleanup()
        log.info("Display cleaned up. Goodbye.")


if __name__ == "__main__":
    main()
