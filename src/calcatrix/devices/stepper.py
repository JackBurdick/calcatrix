import time
from gpiozero import Device, DigitalOutputDevice


class Stepper:
    """stepper"""

    def __init__(
        self,
        # init params
        init_config,
        name="stepper",
    ):
        self.name = name
        self.dir_pin = DigitalOutputDevice(init_config["dir"])
        self.step_pin = DigitalOutputDevice(init_config["_step"])
        self.enable_pin = DigitalOutputDevice(init_config["enable"])
        self.pulse_width = 0.0015
        self.time_between = 0.005

        # ensure stepper off
        self.enable_pin.on()

    def _step(self):
        self.step_pin.on()
        time.sleep(self.pulse_width)
        self.step_pin.off()

    def step_direction(self, direction=True):
        # set direction
        if direction:
            self.dir_pin.on()
        else:
            self.dir_pin.off()
        # take step
        self._step()
        # sleep between steps
        time.sleep(self.time_between)

    def __repr__(self):
        return str(self.__class__.__name__) + ": " + f"{self.__dict__}"
