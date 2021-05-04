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
        self.angle = 10

        self._dist = self._set_angle_dist(self.mm_to_object, self.angle)
        self._angle_a = self.angle / 2
        self._angle_b = 360 - self._angle_a

        self.view_locations = None
        self.instructions = None

    def initialize(self):
        self.view_locations = self._init_locations()
        self.instructions = self._create_instructions()

    def follow_instruction(self, instruction, func=print):
        # move to specified location and angle
        self.linear.move_to_location(instruction["location"])
        self.rotate.move_to(instruction["rot_degree"])

        # perform function if required
        if func:
            if callable(func):
                func(instruction)
            else:
                raise TypeError(f"function {func} is not callable")
        
        # return to zero state
        self.rotate.move_to(0)

    def follow_all_instructions(self, func=None):
        if not self.instructions:
            raise ValueError(f"No instructions present")
        for instruction in self.instructions:
            self.follow_instruction(instruction, func=func)

    def _set_angle_dist(self, dist, angle):
        travel =  math.tan(angle * math.pi / 180) * dist
        return travel

    def _create_instructions(self):
        """
        create sorted list of locations to stop + corresponding instructions to perform

        Rather than jump from location to location, this creates a more efficient route
        that does not require the linear device to "go back"
        """
        instructions = []
        # loop indexes
        for ind, specs in self.view_locations.items():
            # loop locations of each instance
            for name, tup in specs.items():
                instruction = {
                    "location": tup[0],
                    "rot_degree": tup[1],
                    "name": name,
                    "index": ind,
                }
                instructions.append(instruction)

        instructions_sorted = sorted(instructions, key=lambda k: k["location"])

        return instructions_sorted

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
