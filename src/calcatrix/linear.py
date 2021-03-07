import sys
import time

from gpiozero import Device
from calcatrix.devices.hall import Hall
from calcatrix.devices.stepper import Stepper

# from gpiozero.pins.mock import MockFactory
from gpiozero.pins.native import NativeFactory

Device.pin_factory = NativeFactory()

import datetime as dt


class LinearDevice:
    """stepper"""

    def __init__(
        self,
        # init params
        init_config,
        name="linear",
    ):
        self.name = name
        self.stepper = Stepper(init_config["stepper"], name="step")
        self.marker = Hall(**init_config["location"]["marker"], name="marker")
        self.bound_a = Hall(**init_config["location"]["bound_a"], name="a")
        self.bound_b = Hall(**init_config["location"]["bound_b"], name="b")

        self.cur_location = None
        self.dir_dict = {}
        self.max_steps = 500

        # self.set_home()

    def at_location(self):
        return self.marker.value

    def set_home(self):
        # move one direction
        print('moving True')
        o_t = self._move_to_bound(True)
        if o_t[0]:
            home_name = "a"
        else:
            home_name = "b"
        self.dir_dict[home_name] = {"direction": True, "location": 0}

        print('moving other')
        # move the other + and collect marker locations along the way
        o_f = self._move_to_bound(False, collect_markers=True, prev_bound=home_name)
        if o_f[0]:
            end_name = "a"
        else:
            end_name = "b"
        self.dir_dict[end_name] = {"direction": True, "location": o_f[2]}

        # ensure each direction uses a different sensor
        if home_name == end_name:
            raise ValueError(f"bounds appear to share same sensor")

        # override max_steps
        self.max_steps = o_f[2]

        # TODO: some logic with marker locations
        # 1) find connected components
        # 2) take average
        # 3) store averages + use them later

    def _move_to_bound(self, direction, collect_markers=False, prev_bound=None):
        cur_step = 0
        self.stepper.enable_pin.off()
        try:
            while cur_step < self.max_steps:
                if self.bound_a.value or self.bound_b.value:
                    if prev_bound is not None:
                        if prev_bound == "a":
                            if self.bound_b.value:
                                print(f"AT BOUND")
                                break
                        else:
                            if self.bound_a.value:
                                print(f"AT BOUND")
                                break
                    else:
                        print(f"AT BOUND1")
                        break
                else:
                    if collect_markers:
                        if self.marker.value:
                            self.marker.activations.append(cur_step)
                    self.stepper.step_direction(direction)
                    cur_step += 1
            if cur_step == self.max_steps:
                raise ValueError(f"Did not find bounds in max allowed step")
        finally:
            self.stepper.enable_pin.on()

        return (self.bound_a.value, self.bound_b.value, cur_step)

    def move_direction(self, num_steps, direction):
        # turn stepper enable_pin off at start and on at end (opposite logic)
        self.stepper.enable_pin.off()
        cur_step = 0
        try:
            while cur_step < num_steps:
                if self.at_location():
                    print(f"stop - location: {cur_step}")
                    break
                else:
                    self.stepper.step_direction(direction)
                    print(f"{cur_step}/{num_steps} {direction}")
                    cur_step += 1
        finally:
            self.stepper.enable_pin.on()

    def __repr__(self):
        return str(self.__class__.__name__) + ": " + f"{self.__dict__}"
