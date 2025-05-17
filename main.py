from leds import sunrise_led, main_led
from brightness_control import brightness_control
from server import HTTPServer
import logging
import uasyncio
import json
import os


async def log_exceptions(awaitable, s):
    try:
        return await awaitable
    except Exception as e:
        print(e)
        logging.write_to_log(s, e)
        

async def main():
    
    led = machine.Pin('LED', machine.Pin.OUT)
    led.value(True)
    
    print("Running main")

    # Check if the file exists before opening
    if "secrets.json" in os.listdir():
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        print("Error: secrets.json file is required - see README.md")
        raise FileNotFoundError("secrets.json not found")
    
    ssid = secrets["ssid"]
    password = secrets["password"]
    
    server = HTTPServer(ssid, password)

    uasyncio.create_task(log_exceptions(server.start_server(), server))
    uasyncio.create_task(log_exceptions(server.auto_update_time(), server))
    uasyncio.create_task(log_exceptions(logging.write_memory_to_log(server), server))
    uasyncio.create_task(log_exceptions(brightness_control.handle_button(), server))
    uasyncio.create_task(log_exceptions(sunrise_led.handle_button(), server))
    uasyncio.create_task(log_exceptions(main_led.handle_button(), server))
    
    while True:
        await uasyncio.sleep(0.01)


if __name__ == "__main__":
    uasyncio.run(main())
