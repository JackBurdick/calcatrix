from gpiozero import Device  # pylint: disable=import-error
from gpiozero.pins.native import NativeFactory  # pylint: disable=import-error

from calcatrix.devices.hall import Hall
from calcatrix.devices.limit import Limit
from calcatrix.devices.stepper import Stepper

Device.pin_factory = NativeFactory()


class LinearDevice:
    """treader cart"""

    def __init__(
        self,
        # init params
        init_config,
        max_steps=None,
        name="linear",
    ):
        self.name = name
        self.stepper = Stepper(init_config["stepper"], name="step")
        self.marker = Hall(**init_config["location"]["marker"], name="marker")
        self.bound_a = Limit(**init_config["location"]["bound_a"], name="a")
        self.bound_b = Limit(**init_config["location"]["bound_b"], name="b")

        self.cur_location = None
        self.dir_dict = {}

        # TODO: const by hardware
        self.backoff_steps = 40
        self.pulses_per_step = 5

        self.sequence_tolerance = 5

        # 'average' Location of the markers, is set on the set_home() sequence
        self.positions = None
        self._dir_increase = None

        self._pulley_teeth = 20
        self._timing_pitch_mm = 3
        self._steps_per_rev = 400
        self._len_belt_mm = 60000

        self.__len_per_rev = self._pulley_teeth * self._timing_pitch_mm
        self.__mm_per_step = self.__len_per_rev / self._steps_per_rev
        self.__steps_per_belt = self._len_belt_mm / self.__mm_per_step

        if not max_steps:
            self.max_steps = self.__steps_per_belt
        elif isinstance(max_steps, int):
            if max_steps > self.__steps_per_belt:
                raise ValueError(
                    f"max_steps must be less than belt length ({self._len_belt_mm}) / "
                    f"((num_teeth ({self._pulley_teeth}) * pitch (self._timing_pitch_mm))"
                    f" / steps per rev ({self._steps_per_rev}))"
                )
            elif max_steps <= 0:
                raise ValueError(
                    f"please set `max_steps` to a positive value, not {max_steps}"
                )
            else:
                self.max_steps = max_steps
        else:
            raise TypeError(
                f"`max_steps` should be type {int}, not {type(max_steps)} ({max_steps})"
            )

    def at_location(self):
        return self.marker.value

    def _find_seqs_with_tol(self, positions, tolerance=1):
        # https://stackoverflow.com/questions/2361945/detecting-consecutive-integers-in-a-list
        # drop duplicates (shouldn't be present) + ensure sort
        positions = sorted(set(positions))
        gaps = [[s, e] for s, e in zip(positions, positions[1:]) if s + tolerance < e]
        edges = iter(positions[:1] + sum(gaps, []) + positions[-1:])
        return list(zip(edges, edges))

    def _obtain_average_from_seq(self, l, lt):
        positions = {}
        for i, inds in enumerate(lt):
            # NOTE: will round down, e.g. 123.5 --> 123
            avg = int((inds[0] + inds[1]) / 2)
            positions[i] = avg
        return positions

    def _obtain_positions(self, l, tolerance=1):
        lt = self._find_seqs_with_tol(l, tolerance)
        pos = self._obtain_average_from_seq(l, lt)
        return pos

    def set_home(self):
        # move one direction
        print("moving True")
        o_t = self._move_to_bound(True)
        if o_t[0]:
            home_name = "a"
        else:
            home_name = "b"
        self.dir_dict[home_name] = {"direction": True, "location": 0}

        print("moving other")
        # move the other + and collect marker locations along the way
        o_f = self._move_to_bound(False, collect_markers=True, prev_bound=home_name)
        if o_f[0]:
            end_name = "a"
        else:
            end_name = "b"
        self._dir_increase = False
        self.dir_dict[end_name] = {"direction": False, "location": o_f[2]}

        # ensure each direction uses a different sensor
        if home_name == end_name:
            raise ValueError("bounds appear to share same sensor")

        # override max_steps
        self.max_steps = o_f[2]

        if self.marker.activations:
            self.positions = self._obtain_positions(
                self.marker.activations, self.sequence_tolerance
            )

    def _backoff_bound(self, cur_direction):
        opp_direction = not cur_direction
        for _ in range(self.backoff_steps):
            self.stepper.step_direction(opp_direction)
            # TODO: ensure backoff

    def _move_to_bound(self, direction, collect_markers=False, prev_bound=None):
        cur_step = 0
        self.stepper.enable_pin.off()
        a_val, b_val = False, False
        try:
            while cur_step < self.max_steps:
                self.stepper.step_direction(direction)
                cur_step += 1
                if cur_step % self.pulses_per_step == 0:
                    # TODO: this logic can likely be improved
                    if self.bound_a.value or self.bound_b.value:
                        if prev_bound is not None:
                            if prev_bound == "a":
                                if self.bound_b.value:
                                    print("AT BOUND 2 (B)")
                                    a_val, b_val = (
                                        self.bound_a.value,
                                        self.bound_b.value,
                                    )
                                    self._backoff_bound(direction)
                                    break
                            else:
                                if self.bound_a.value:
                                    a_val, b_val = (
                                        self.bound_a.value,
                                        self.bound_b.value,
                                    )
                                    print("AT BOUND 2 (A)")
                                    self._backoff_bound(direction)
                                    break
                        else:
                            print("AT BOUND 1")
                            a_val, b_val = self.bound_a.value, self.bound_b.value
                            self._backoff_bound(direction)
                            break
                    else:
                        if collect_markers:
                            if self.marker.value:
                                self.marker.activations.append(cur_step)

            if cur_step >= self.max_steps:
                raise ValueError("Did not find bounds in max allowed step")
        finally:
            self.stepper.enable_pin.on()

        return (a_val, b_val, cur_step)

    def move_direction(self, num_steps, direction):
        # turn stepper enable_pin off at start and on at end (opposite logic)
        self.stepper.enable_pin.off()

        if direction == self._dir_increase:
            op = int.__add__
        else:
            op = int.__sub__

        end_position = op(self.cur_location, num_steps)
        if end_position > self.max_steps or end_position < 0:
            raise ValueError(
                f"move_direction({num_steps}, {direction}) from {self.cur_location}, "
                f"will land at {end_position}, which is outside [0, {self.max_steps}]"
            )

        cur_step = 0
        try:
            while cur_step <= num_steps:
                cur_step += 1
                self.stepper.step_direction(direction)
                if cur_step % self.pulses_per_step == 0:
                    if self.bound_a.value or self.bound_b.value:
                        raise ValueError(
                            f"Unexpected bound: or obstacle. cur:{self.cur_location}, [0,{self.max_steps}]"
                        )
        finally:
            self.stepper.enable_pin.on()

    def move_to_index(self, index, unsafe=False):
        # turn stepper enable_pin off at start and on at end (opposite logic)
        self.stepper.enable_pin.off()

        try:
            ind_position = self.positions[index]
        except KeyError:
            raise ValueError(
                f"Desired index is not available. Please select from {self.positions.keys()}"
            )

        num_steps = self.cur_location - ind_position
        if num_steps > 0:
            dir_to_index = self._dir_increase
        else:
            dir_to_index = not self._dir_increase

        if not dir_to_index:
            raise ValueError(
                f"Linear device has not been homed and does not know direction to index"
            )

        self.move_direction(num_steps, dir_to_index)

        if not unsafe:
            if not self.at_location():
                raise ValueError(
                    "Should be at a location, but not registering at a location"
                    f"\n  cur_location: {self.cur_location}"
                    f"\n  ind_position: {ind_position}"
                    f"\n  bounds: [0,{self.max_steps}]"
                    f"\n  at_location: {self.at_location()}"
                )

    def __repr__(self):
        return str(self.__class__.__name__) + ": " + f"{self.__dict__}"
