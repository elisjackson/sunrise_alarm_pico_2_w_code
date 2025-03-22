from machine import Pin
import time
import uasyncio


class BrightnessControl:
    
    def __init__(self, pin: int):
        
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.event = uasyncio.Event()
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self.button_irq)
        self.control_direction = 1
        self.brightness = 0.05


    def button_irq(self, pin):
        self.event.set()


    async def handle_button(self):
        
        while True:

            await self.event.wait()

                 
            # Debouncing - wait for pin to change value
            # it needs to be stable for a continuous 35ms
            active = 0
            while active < 35:            
                if self.pin.value() == 0:
                    active += 1
                else:
                    active = 0
                await uasyncio.sleep(0.001)
            
            # Increase/Decrease brightness
            while self.pin.value() == 0:
                
                self.brightness += 0.01 * self.control_direction
                # print(round(self.brightness, 3))
                
                if self.brightness <= 0:
                    self.brightness = 0
                    break
                elif self.brightness >= 1:
                    self.brightness = 1
                    break
                else:                    
                    await uasyncio.sleep(0.025)
            
            # TODO - cap the brightness according to max current limits
            
            # flip direction setting ready for next press
            self.control_direction = self.control_direction * -1
            # Reset event flag for next press
            self.event.clear()


brightness_control = BrightnessControl(pin=22)