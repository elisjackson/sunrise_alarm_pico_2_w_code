from brightness_control import brightness_control
import neopixel
import time
from machine import Pin, RTC
import uasyncio


class LEDController:

    def __init__(
        self,
        leds_pin: int,
        mode_button_pin: int,
        number_of_leds: int,
        led_function,  # "normal" or "sunrise"
        led_type,  # "rgb" or "rgbw"
        alarm_time: tuple = (6, 35),
        ):
        """
        
        """

        self.led_function = led_function
        self.led_type = led_type

        # LED attributes
        self.number_of_leds = number_of_leds
        
        self.neopix = neopixel.NeoPixel(
            Pin(leds_pin),
            number_of_leds,
            bpp=4 if led_type == "rgbw" else 3,
            )

        # Toggle control button attributes
        self.mode_button = Pin(mode_button_pin, Pin.IN, Pin.PULL_UP)
        self.button_event = uasyncio.Event()
        self.last_press_time = time.ticks_ms()  # Initialise with current time
        self.mode_button.irq(trigger=Pin.IRQ_FALLING, handler=self.button_irq)

        if led_function == "sunrise":
        
            self.led_options = [
                "off",
                "white",
                "rainbow",
                "sunrise_alarm",
                ]
            
        else:
            
            self.led_options = [
                "off",
                "white",
                "rainbow",
            ]
        
        # Initialise mode cycle generator
        self.led_cycle_gen = self.cycle(self.led_options)
        # Initialise mode - it will take the first item from self.led_options
        self.mode = next(self.led_cycle_gen)
        
        self.current_control_task = None
        
        # alarm settings
        self.alarm_time = alarm_time

     
    def button_irq(self, pin):
        self.button_event.set()

    
    async def handle_button(self):
        while True:
            await self.button_event.wait()
            
            # Debouncing - wait for pin to change value
            # it needs to be stable for a continuous 50ms
            cur_value = self.mode_button.value()
            active = 0
            while active < 50:
                if self.mode_button.value() != cur_value:
                    active += 1
                else:
                    active = 0
                time.sleep(0.001)
            
            # Cancel the current LED task before switching modes
            if self.current_control_task:
                self.current_control_task.cancel()
                try:
                    # Ensure it's properly awaited before continuing
                    await self.current_control_task
                except uasyncio.CancelledError:
                    pass  # Task was cancelled
                
            self.mode = next(self.led_cycle_gen)
            self.current_control_task = uasyncio.create_task(self.control_led())
            self.button_event.clear()  # Reset event flag for next press
            
            
    async def handle_server_mode_control(self, mode):
        """
        """
        
        self.mode = mode
        
        # Cancel the current LED task before switching modes
        if self.current_control_task:
            self.current_control_task.cancel()
            try:
                # Ensure it's properly awaited before continuing
                await self.current_control_task
            except uasyncio.CancelledError:
                pass  # Task was cancelled
        
        self.current_control_task = uasyncio.create_task(self.control_led())
        
        
    def handle_server_alarm_time_update(self, time):
        """
        time: tuple (hour[int], minute[int])
        """
        self.alarm_time = time


    def cycle(self, iterable):
        """
        Custom cycle generator, avoiding memory leak if using itertools.cycle()
        """
        iterator = iter(iterable)
        while True:
            try:
                yield next(iterator)
            except StopIteration:
                iterator = iter(iterable)
                
    
    async def control_led(self):
        """
        Trigger different modes for the LED
        """
        
        if self.mode == "off":
            self.turn_off()
            
        elif self.mode == "white":
            await self.turn_on()
            
        elif self.mode == "rainbow":
            await self.turn_on_rainbow()
            
        elif self.mode == "sunrise_alarm":
            self.turn_off()
            await self.turn_on_sunrise_mode()
                
                
    def adjust_for_rgbw(self, col: list, off=False):
        """
        Adjust RGB input to RGBW, if the LEDs are of RGBW type.

        Args:
            col: list containing RGB values
            off: boolean flag, indicating whether the LEDs should be "on" (in any mode) of "off"
        """
        
        if type(col) != list:
            col = list(col)
            
        if self.led_type == "rgbw":
            if off:
                col.append(0)
            else:
                col.append(255)
                
        return col
        
                
    def adjust_brightness(self, col: list):
        """
        Adjusts the LED brightness according to the live current brightness setting.

        Args:
            col: list of RGB or RGBW values
        """
        
        return [c * brightness_control.brightness for c in col]
    
    
    def write_all_leds(self, col: list):
        """
        Writes the same RGB/RGBW data to all LEDs in the string.

        Args:
            col: desired RGB/RGBW values for all LEDs.
        """

        col = [int(c) for c in col]  # ensure all integers
        col = tuple(col)  # list to tuple
        for i in range(self.number_of_leds):
            self.neopix[i] = col
        self.neopix.write()
                
                
    def turn_off(self):
        """
        Turn off all LEDs.
        """
        col = [0, 0, 0]
        col = self.adjust_for_rgbw(col, off=True)
        self.write_all_leds(col)
        
        
    async def turn_on(self, rgb: tuple=None):
        """
        Turn on all LEDs in the string to a steady colour. Defaults to white.

        Args:
            rgb: the desired rgb colour
        """
        
        while True:
        
            if not rgb:
                # default to white
                col = [255, 255, 255]
                
            col = self.adjust_for_rgbw(col)
            col = self.adjust_brightness(col)
            self.write_all_leds(col)
            
            await uasyncio.sleep(0.025)
        
        
    def interpolate_points_gen(
        self,
        vertices: list[int],
        minor_time_steps: int
        ):
        """
        TODO - docstring
        """
        
        # initialize generator & step forward
        vertices_generator = self.cycle(vertices)
        next(vertices_generator)
        
        # v0 = start value; v1 = end value
        for v0 in vertices:
            # reset minor_time_step counter
            minor_time_step = 0
            v1 = next(vertices_generator)
            # calculate linear slope
            m = (v1 - v0) / minor_time_steps
            while minor_time_step < minor_time_steps:
                # calculate interpolated vertex
                vx = v0 + (m * minor_time_step)
                minor_time_step += 1
                yield vx
            
        
    def rainbow_gen(
        self,
        refresh_rate: float,
        cycle_period: float,
        ):
        """
        TODO - docstring
        """
        
        # define rgb colours at 100% brightness
        RED = (255, 0, 0)
        YELLOW = (255, 150, 0)
        GREEN = (0, 255, 0)
        CYAN = (0, 255, 255)
        BLUE = (0, 0, 255)
        PURPLE = (180, 0, 255)
        
        discrete_colour_cycle = [
            RED,
            YELLOW,
            GREEN,
            CYAN,
            BLUE,
            PURPLE
            ]
        
        len_colours = len(discrete_colour_cycle)
        total_time_steps = cycle_period / refresh_rate
        # minor_time_steps: count of time steps within a single colour change
        # e.g. from RED to YELLOW
        # add one to len_colours to account for "last" to "first" transition
        minor_time_steps = int(total_time_steps / (len_colours + 1))

        # Now, take discrete list, and make long list.
        # Preferably as a generator object.
        # Return the generator object.

        discrete_colour_cycle_gen = self.cycle(discrete_colour_cycle)
        
        # this creates what can be pictured, for each element that is R, G, and B,
        # a set of "vertices" on a "value-time" graph
        rgb_vertices = [[], [], []]
        # for i in range(len_colours) + 1):
        for i in range(len_colours):
            colour = next(discrete_colour_cycle_gen)
            for j in range(len(rgb_vertices)):
                rgb_vertices[j].append(colour[j])
                
        # create a generator each for R G and B
        rgb_gen = []
        for vertices in rgb_vertices:
            rgb_gen.append(
                self.interpolate_points_gen(
                    vertices,
                    minor_time_steps
                    )
                )
        
        return rgb_gen
    
        
    async def turn_on_rainbow(self):
        """
        TODO - docstring
        """
        
        refresh_rate = 0.05  # seconds
        cycle_period = 5  # seconds from RED to PURPLE
                
        rgb_gens = self.rainbow_gen(refresh_rate, cycle_period)
        
        while True:
            
            try:            
                col = [
                    next(rgb_gens[0]),
                    next(rgb_gens[1]),
                    next(rgb_gens[2]),
                    ]
            except StopIteration:
                rgb_gens = self.rainbow_gen(refresh_rate, cycle_period)
                col = [
                    next(rgb_gens[0]),
                    next(rgb_gens[1]),
                    next(rgb_gens[2]),
                    ]
                
            col = self.adjust_for_rgbw(col)
            col = self.adjust_brightness(col)
            self.write_all_leds(col)
            await uasyncio.sleep(refresh_rate)
            
            
    async def fadeout_leds(self, fade_duration: float = 1):
        """
        Gradually fade out the LEDs to "off"

        Args:
            fade_duration: time taken to fade to off (seconds)
        """
        
        time_resolution = 0.01
        
        # get the starting state
        start_rgb = []
        for i in range(self.number_of_leds):
            start_rgb.append(self.neopix[i])
        
        # loop through time steps, write fade
        t = 0
        while t < fade_duration:
            t_ratio = t / fade_duration
            for i in range(self.number_of_leds):
                rgb_t = [int(c * (1 - t_ratio)) for c in start_rgb[i]]
                rgb_t = tuple(rgb_t)
                self.neopix[i] = rgb_t
            self.neopix.write()
            await uasyncio.sleep(time_resolution)
            t += time_resolution
        
        # ensure off at end
        self.turn_off()            
            
            
    async def flash_clock(
        self,
        value: int,
        time_type: str,  # "hour" or "minute"
        rgb: list[int]
        ):
        """
        Feedback the set alarm time hour or minute.

        Lights the LEDs to the 'clock face' value corresponding to the hour/minute value passed.
        Examples:
        - flash_clock(3, "hour", [0, 0, 255]) -> light LEDs in blue from the 12 to the 3 o'clock positions
        - flash_clock(25, "minute", [255, 0, 0]) -> light LEDs in red from the 12 to the 5 o'clock positions

        Args:
            value: hour or minute value
            time_type: "hour" or "minute", used to apply correct conversion to the 'clock face' value
            rgb: desired LED colour
        """
        
        # adjust rgb input
        col = self.adjust_for_rgbw(rgb)
        col = self.adjust_brightness(col)
        col = [int(c) for c in col]  # ensure all integers
        col = tuple(col)  # list to tuple
        
        # TODO - change this to work with variable number of LEDs on ring
        if time_type == "hour":
            value = (value % 12)
        elif time_type == "minute":
            value = int(round((value / 60) * 12))
        
        # clock hand "at 12" - light entire clock face
        if value == 0:
            value = 11
                 
        # increment on LEDs up to the "clock face value"
        for i in range(value + 1):
            self.neopix[i] = col
            self.neopix.write()
            await uasyncio.sleep(0.1)
        
        # hold the final "clock face value" for readability
        await uasyncio.sleep(0.75)
            
        # Add fadeout after minute flash
        if time_type == "minute":
            await self.fadeout_leds()
        
        self.turn_off()        
            
            
    async def flash_alarm_time_indicator(self, alarm_time: tuple[int, int]):
        """
        Show the set alarm hour and minute via the LEDs.

        Args:
            alarm_time: tuple containing alarm time hour and minute.
        """
        await self.flash_clock(alarm_time[0], "hour", [255, 150, 0])
        await self.flash_clock(alarm_time[1], "minute", [0, 0, 255])
        
        
    def get_seconds_to_alarm(self, alarm_time: tuple, start_fadein_offset: int):
        # get current hour and minute
        time_now = RTC().datetime()[4:6]
        
        diff_minutes = alarm_time[1] - time_now[1]
        diff_hours = 24 - time_now[0] + alarm_time[0]
                
        if diff_hours == 24:
            if diff_minutes > 0:
                diff_hours = 0
        else:
            diff_hours = diff_hours % 24

        alarm_countown_seconds = (3600 * diff_hours) + (60 * diff_minutes)
        alarm_countown_seconds = alarm_countown_seconds - start_fadein_offset
        # ensure countdown cannot be negative
        alarm_countown_seconds = max(0, alarm_countown_seconds)
        
        return alarm_countown_seconds
    
    
    async def alarm_mode(self, seconds_remaining: int):
        
        await uasyncio.sleep(seconds_remaining)
        
        print("Alarm on at", RTC().datetime())
        
        # all in seconds
        time_resolution = 0.1
        fadein_duration = 20 * 60
        fadeout_duration = 3600
        
        time_steps = int(fadein_duration / time_resolution)
        
        # boost the brightness - TODO - keep or discard this?
        # max_brightness = min(1.5 * self.brightness, 0.75)
        max_brightness = brightness_control.brightness
        print(max_brightness)
        
        colour = (255, 255, 102)  # light yellow
        
        step = 0
        while step < time_steps:
            brightness = (step / time_steps) * max_brightness
            col = self.adjust_for_rgbw(colour)
            col = [c * brightness for c in col]
            self.write_all_leds(col)            
            step += 1
            await uasyncio.sleep(time_resolution)
            
        # fade out slowly
        await self.fadeout_leds(fade_duration=fadeout_duration)
        self.turn_off()  # ensure all off at end
            
            
    async def turn_on_sunrise_mode(self):
        """
        Handle LED when sunrise mode is selected.

        1. Turn off LEDs (assuming they may already be lit)
        2. Feedback the current alarm time
        3. Calculate time to wait, and sleep for desired amount of time
        4. Execute the sunrise wake-up coroutine
        """
        
        self.turn_off()
        timer_refresh_period = 3600
        start_offset_seconds = 5 * 60
        
        # Display the alarm time
        await self.flash_alarm_time_indicator(self.alarm_time)
        
        # initialize to enter while loop
        seconds_remaining = timer_refresh_period + 1
        
        while True:
            seconds_remaining = self.get_seconds_to_alarm(self.alarm_time, start_offset_seconds)                
            print(f"Sleeping for {seconds_remaining} seconds")
            if seconds_remaining > timer_refresh_period + start_offset_seconds:
                await uasyncio.sleep(timer_refresh_period)
            else:
                await uasyncio.create_task(self.alarm_mode(seconds_remaining))


sunrise_led = LEDController(
        leds_pin=4,
        mode_button_pin=12,
        number_of_leds=12,
        led_function="sunrise",
        led_type = "rgbw",
    )

main_led = LEDController(
        leds_pin=22,
        mode_button_pin=19,
        number_of_leds=12, 
        led_function="normal",
        led_type = "rgb",
    )