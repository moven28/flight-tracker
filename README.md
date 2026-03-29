# ✈ E-Ink Flight Tracker – Setup Guide
# Raspberry Pi Zero W + Waveshare E-Ink display

## Hardware needed
- Raspberry Pi Zero W (or Zero 2 W)
- Waveshare e-Paper display (2.13", 2.9", 4.2" or 7.5" HAT)
- MicroSD card (8 GB+), MicroUSB power supply

---

## 1. Enable SPI on the Pi

```bash
sudo raspi-config
# → Interface Options → SPI → Enable
sudo reboot
```

---

## 2. Install system packages

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv fonts-dejavu-core git
```

---

## 3. Clone Waveshare e-Paper library

```bash
cd ~
git clone https://github.com/waveshare/e-Paper.git
cp -r e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd \
      ~/flight_tracker/waveshare_epd
```

---

## 4. Install Python dependencies

```bash
cd ~/flight_tracker
python3 -m venv venv
source venv/bin/activate
pip install requests Pillow RPi.GPIO spidev
```

---

## 5. Configure your location & display

Edit `config.py`:
- Set `BOUNDING_BOX` to your lat/lon area (default is Lynnwood, WA)
- Uncomment the `DISPLAY_MODEL` line that matches your screen
- Set `DISPLAY_WIDTH` / `DISPLAY_HEIGHT` to match

---

## 6. Test without the display (saves PNG to /tmp)

```bash
source venv/bin/activate
python3 main.py --demo          # dummy data, no API call
python3 main.py --test          # live API call, saves PNG
```

---

## 7. Run live

```bash
python3 main.py
```

---

## 8. Auto-start on boot (systemd)

Copy the service file:
```bash
sudo cp flight-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable flight-tracker
sudo systemctl start flight-tracker
```

Check logs:
```bash
journalctl -u flight-tracker -f
```

---

## OpenSky API rate limits

| Mode            | Requests/day | Interval   |
|-----------------|-------------|------------|
| Anonymous       | ~100        | Every 10 s minimum (enforced) |
| Free account    | 4,000       | Every 10 s |
| Premium         | 10,000+     | Every 1 s  |

Register free at https://opensky-network.org and set
`OPENSKY_USER` / `OPENSKY_PASS` in config.py for a much
higher quota.

---

## Project structure

```
flight_tracker/
├── config.py          ← location, display settings, airline map
├── fetcher.py         ← OpenSky API client
├── renderer.py        ← Pillow image renderer
├── main.py            ← poll loop + e-ink driver wrapper
├── README.md          ← this file
├── flight-tracker.service
└── waveshare_epd/     ← copied from Waveshare repo
    └── epd4in2.py     (and others)
```
