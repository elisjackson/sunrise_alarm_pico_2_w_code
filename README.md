# Sunrise alarm clock

This repo contains Micropython code written for use on a Raspberry Pi Pico 2 W.\
See [elisjackson.github.io](https://elisjackson.github.io/projects/sunrise-alarm-clock/) for a more detailed project write up.

The code:
- handles the independent control of two LED strings. Lighting modes are defined (and can be modified or added to) `leds.py`
- initialises a small HTTP server on the Pi Pico. Navigating to the server's IP address in a browser serves a webpage (defined in `index.html`) which allows control of the LED strings (setting the alarm time, setting lighting modes, and brightness settings).

Other repositories associated with this project:
- [KiCAD PCB files](https://github.com/elisjackson/sunrise_alarm_kicad)

## Pico setup

1. [Flash MicroPython](https://micropython.org/download/RPI_PICO2_W/) to the Pico
2. Clone this repository
3. Add a file named `secrets.json`. Populate it with:
```
{
    "ssid": "Your-WiFi-SSID",
    "password": "Your-WiFi-Password"
}
```
4. Upload the contents of this repository to the Pico.
   * See [pico_bulk_upload](https://github.com/elisjackson/pico_bulk_upload) for code to easily upload all files
