from gpiozero import Device  # pylint: disable=import-error
from gpiozero.pins.native import NativeFactory  # pylint: disable=import-error

from calcatrix.devices.linear import LinearDevice
from calcatrix.devices.rotate import Rotator

import math

Device.pin_factory = NativeFactory()


class MultiView:
    """multiview cart"""

    def __init__(
        self,
        # init params
        init_config,
        max_steps=None,
        name="linear",
    ):
        self.name = name
        self.linear = LinearDevice(init_config["linear"])
        self.rotate = Rotator(init_config["rotate"]["pins"])

        self.mm_to_object = 300
        self.angle = 30

        self._dist = self._set_angle_dist(30)
        self._angle_a = angle / 2
        self._angle_b = 360 - self._angle_a

        self.view_locations = self.init_locations()

    def _set_angle_dist(self, dist, angle):
        return math.tan(angle * math.pi / 180) * dist

    def init_locations(self):
        self.linear.set_home()

        if not self.linear.positions:
            raise ValueError("No positions present")

        view_locs = {}
        for ind, iloc in self.linear.positions.items():
            # NOTE: unsure what the keys should be here
            loc_d = {
                "a": (iloc - self._dist, self._angle_a),
                "0": (iloc, 0),
                "b": (iloc + self._dist, self._angle_b),
            }
            view_locs[ind] = loc_d
        return view_locs

    def __repr__(self):
        return str(self.__class__.__name__) + ": " + f"{self.__dict__}"