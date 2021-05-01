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

        self.view_locations = None
        self.instructions = None

    def initialize(self):
        self.view_locations = self._init_locations()
        self.instructions = self._create_instructions()

    def _set_angle_dist(self, dist, angle):
        return math.tan(angle * math.pi / 180) * dist

    def _create_instructions(self):
        """
        each instruction will contain
        (location, degree_to_rotate, location_name, index)

        e.g.
            [
                (70, -15, '-', 0),
                (100, 0, '0', 0),
                (130, 15, '+', 0),
                ...
            ]
        """
        instructions = []
        # loop indexes
        for ind, specs in self.view_locations.items():
            # loop locations of each instance
            for name, tup in specs.items():
                instruction = (tup[0], tup[1], name, ind)
                instructions.append(instruction)
        return instructions

    def _init_locations(self):
        self.linear.set_home()

        if not self.linear.positions:
            raise ValueError("No positions present")

        view_locs = {}
        for ind, iloc in self.linear.positions.items():
            # NOTE: unsure what the keys should be here
            loc_d = {
                "-": (iloc - self._dist, self._angle_a),
                "0": (iloc, 0),
                "+": (iloc + self._dist, self._angle_b),
            }
            view_locs[ind] = loc_d
        return view_locs

    def __repr__(self):
        return str(self.__class__.__name__) + ": " + f"{self.__dict__}"
