from leds import sunrise_led #, main_led
from brightness_control import brightness_control
from server import HTTPServer
import logging
import uasyncio
import json
import time


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
    
    # TODO - error handle this. Check it exists.
    # If not - don't run server.
    with open("secrets.json") as f:
        secrets = json.load(f)
    
    ssid = secrets["ssid"]
    password = secrets["password"]
    
    server = HTTPServer(ssid, password)
    
    """
    uasyncio.create_task(server.start_server())
    uasyncio.create_task(server.auto_update_time())
    uasyncio.create_task(logging.write_memory_to_log(server))
    uasyncio.create_task(brightness_control.handle_button())
    uasyncio.create_task(sunrise_led.handle_button())
    uasyncio.create_task(main_led.handle_button())
    """
    uasyncio.create_task(log_exceptions(server.start_server(), server))
    uasyncio.create_task(log_exceptions(server.auto_update_time(), server))
    uasyncio.create_task(log_exceptions(logging.write_memory_to_log(server), server))
    uasyncio.create_task(log_exceptions(brightness_control.handle_button(), server))
    uasyncio.create_task(log_exceptions(sunrise_led.handle_button(), server))
    # uasyncio.create_task(log_exceptions(main_led.handle_button(), server))
    
    while True:
        await uasyncio.sleep(0.01)


if __name__ == "__main__":
    uasyncio.run(main())
