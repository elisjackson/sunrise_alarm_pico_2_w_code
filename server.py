import network
import ntptime
from time import sleep
import machine
import rp2
import sys
import uasyncio
from index import webpage
from brightness_control import brightness_control
from leds import sunrise_led, main_led


class HTTPServer:
    
    def __init__(self, ssid, password):
        
        self.ssid = ssid
        self.password = password
        self.pico_led = machine.Pin("LED", machine.Pin.OUT)
        
        self.rtc = machine.RTC()
        
        self.ip = self.connect()
        
        
    def update_time(self):
        
        ntptime.host = "1.europe.pool.ntp.org"
        print()

        try:
            print("RTC pre-synchronization", self.rtc.datetime())
            
            ntptime.settime()
            print("RTC post-synchronization ", self.rtc.datetime())
        
        except Exception as e:
          print("Error syncing time", e)
        
        
    async def auto_update_time(self):
        
        while True:
            self.update_time()
            await uasyncio.sleep(60 * 60)
        
        
    async def start_server(self):
        print("Starting server...")
        server = await uasyncio.start_server(self.serve_client, "0.0.0.0", 80)


    def connect(self):
        #Connect to WLAN
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        print("In connect()")
        
        print("wlan.connect() complete")
        print(wlan.isconnected())
        
        wlan.connect(self.ssid, self.password)
        
        timeout = 100  # 10 seconds
        
        while not wlan.isconnected() and timeout > 0:
            print('Waiting for connection...')
            self.pico_led.toggle()
            sleep(0.25)
            timeout -= 1
            
        if not wlan.isconnected():
            print("Failed to connect to Wi-Fi")
            return None  # Return None if connection fails
        
        print("setting IP")
        ip = wlan.ifconfig()[0]
        print(f'Connected on {ip}')
        
        self.pico_led.value(False)
        
        return ip
    

    async def serve_client(self, reader, writer):
        #Start a web server

        request = await reader.read(1024)
        request = request.decode('utf-8')  # Decode bytes to string
        
        if request[:4] == "POST":

            request_args = request.split()[-1]
            arguments = []
            for a in request_args.split("&"):
                arguments.append(a.split("=")[1])
            
            print("Request arguments:", arguments)
            
            brightness, alarm_time, sunrise_led_mode, main_led_mode = arguments
            # brightness, alarm_time, sunrise_led_mode = arguments
            
            # process brightness; convert % str to decimal
            brightness_control.brightness = int(brightness) / 100
            
            # process & handle LED mode arguments
            sunrise_led_mode = sunrise_led_mode.lower()
            main_led_mode = main_led_mode.lower()
            
            if sunrise_led_mode == "alarm":
                sunrise_led_mode = "sunrise_alarm"
                
            await sunrise_led.handle_server_mode_control(sunrise_led_mode)
            await main_led.handle_server_mode_control(main_led_mode)
            
            # process time
            alarm_hour = int(alarm_time.split("%3A")[0])
            alarm_minute = int(alarm_time.split("%3A")[1])
            alarm_time_tuple = (alarm_hour, alarm_minute)
            sunrise_led.handle_server_alarm_time_update(alarm_time_tuple)
            print()
            
        # Generate the HTML response
        response = webpage(
            int(100 * brightness_control.brightness),
            sunrise_led.alarm_time,
            sunrise_led.mode,
            main_led.mode
            )

        # Send HTTP response
        writer.write("HTTP/1.1 200 OK\r\n")
        writer.write("Content-Type: text/html\r\n")
        writer.write("Connection: close\r\n\r\n")
        writer.write(response)
        await writer.drain()  # Ensure all data is sent

        # Close the connection
        writer.close()
        await writer.wait_closed()


